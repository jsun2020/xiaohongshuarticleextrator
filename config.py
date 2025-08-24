import os
import json
from typing import Optional, Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self._get_default_config()
        else:
            # 创建默认配置文件
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "deepseek": {
                "api_key": "",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "app": {
                "debug": True,
                "auto_save": True,
                "max_recreate_length": 500
            }
        }
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        
        # 创建嵌套字典路径
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存到文件
        self._save_config(self.config)
    
    def get_deepseek_config(self) -> Dict[str, Any]:
        """获取DeepSeek API配置"""
        return self.get('deepseek', {})
    
    def set_deepseek_api_key(self, api_key: str) -> None:
        """设置DeepSeek API Key"""
        self.set('deepseek.api_key', api_key)
    
    def validate_deepseek_config(self) -> bool:
        """验证DeepSeek配置是否完整"""
        api_key = self.get('deepseek.api_key')
        return bool(api_key and api_key.strip())

# 全局配置实例
config = Config()

if __name__ == "__main__":
    # 测试配置功能
    print("🔧 测试配置管理...")
    print(f"DeepSeek API Key: {config.get('deepseek.api_key') or '未设置'}")
    print(f"配置验证: {'✅ 通过' if config.validate_deepseek_config() else '❌ 失败'}")
    print(f"完整配置: {config.config}")
