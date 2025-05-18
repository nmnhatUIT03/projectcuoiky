import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import scipy.stats as stats

def analyze_feature_importance(df_real, synthetic_data, df_benign=None, n_features=20):
    """
    Analyze and compare feature importance between real and synthetic data
    
    Parameters:
    - df_real: DataFrame with real data samples
    - synthetic_data: DataFrame with synthetic data samples
    - df_benign: Optional DataFrame with benign samples (not used for comparison, kept for backward compatibility)
    - n_features: Number of top features to display
    
    Returns:
    - Dictionary with feature importance analysis results
    """
    try:
        # Make copies to avoid modifying original dataframes
        df_real = df_real.copy()
        synthetic_data = synthetic_data.copy()
        
        # Get common columns that we can use for both datasets (excluding labels and metadata)
        common_cols = list(set(df_real.columns) & set(synthetic_data.columns))
        common_cols = [col for col in common_cols if col not in ['label', 'label_numeric', 'is_synthetic']]
        
        if len(common_cols) == 0:
            print("Error: No common feature columns found between real and synthetic data.")
            return {
                'real_importance': None, 
                'synthetic_importance': None,
                'spearman_correlation': None, 
                'p_value': None,
                'visualization_fig': None
            }
        
        # Split data
        X_real = df_real[common_cols]
        y_real = df_real['label_numeric'] if 'label_numeric' in df_real else np.ones(len(df_real))
        
        X_synth = synthetic_data[common_cols]
        y_synth = synthetic_data['label_numeric'] if 'label_numeric' in synthetic_data else np.ones(len(synthetic_data))
        
        # Train XGBoost for feature importance
        model_real = xgb.XGBClassifier(use_label_encoder=False, 
                                      eval_metric='logloss', 
                                      random_state=42)
        model_real.fit(X_real, y_real)
        
        model_synth = xgb.XGBClassifier(use_label_encoder=False, 
                                       eval_metric='logloss', 
                                       random_state=42)
        model_synth.fit(X_synth, y_synth)
        
        # Get feature importance
        real_importance = model_real.feature_importances_
        synth_importance = model_synth.feature_importances_
        
        # Create DataFrames for visualization
        real_imp_df = pd.DataFrame({
            'feature': X_real.columns,
            'importance': real_importance
        }).sort_values('importance', ascending=False).head(min(n_features, len(X_real.columns)))
        
        synth_imp_df = pd.DataFrame({
            'feature': X_synth.columns,
            'importance': synth_importance
        }).sort_values('importance', ascending=False).head(min(n_features, len(X_synth.columns)))
        
        # Visualize
        fig, axes = plt.subplots(1, 2, figsize=(20, 10))
        
        sns.barplot(x='importance', y='feature', data=real_imp_df, ax=axes[0])
        axes[0].set_title('Feature Importance (Real Data)')
        
        sns.barplot(x='importance', y='feature', data=synth_imp_df, ax=axes[1])
        axes[1].set_title('Feature Importance (Synthetic Data)')
        
        plt.tight_layout()
        
        # Calculate similarity between importance rankings
        common_features = set(real_imp_df['feature']) & set(synth_imp_df['feature'])
        
        # Create dictionaries mapping features to their ranks
        real_ranks = {feature: i for i, feature in enumerate(real_imp_df['feature'])}
        synth_ranks = {feature: i for i, feature in enumerate(synth_imp_df['feature'])}
        
        # Calculate Spearman correlation for common features
        spearman_corr = None
        p_value = None
        
        if len(common_features) > 1:  # Need at least 2 values for correlation
            real_importance_common = [real_ranks.get(feature) for feature in common_features]
            synth_importance_common = [synth_ranks.get(feature) for feature in common_features]
            
            spearman_corr, p_value = stats.spearmanr(real_importance_common, synth_importance_common)
        
        return {
            'real_importance': real_imp_df,
            'synthetic_importance': synth_imp_df,
            'visualization_fig': fig,
            'spearman_correlation': spearman_corr,
            'p_value': p_value
        }
    except Exception as e:
        print(f"Error in analyze_feature_importance: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return empty results with correct structure
        return {
            'real_importance': None, 
            'synthetic_importance': None,
            'spearman_correlation': None, 
            'p_value': None,
            'visualization_fig': None
        } 