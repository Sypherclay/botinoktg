"""
АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ВСЕХ КОМАНД
Просто кидай файлы в папку commands/ - они сами загрузятся!
"""
import os
import importlib
from logger import log_bot_event

def register_all_commands(app):
    """Регистрирует все команды из папки commands/"""
    commands_dir = os.path.dirname(__file__)
    loaded_count = 0
    
    print("\n" + "="*50)
    print("📦 ЗАГРУЗКА КОМАНД:")
    print("="*50)
    
    for filename in sorted(os.listdir(commands_dir)):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'commands.{module_name}')
                
                # Если есть функция register - вызываем её
                if hasattr(module, 'register'):
                    module.register(app)
                    loaded_count += 1
                    print(f"  ✅ {module_name}")
                # Если есть список handlers
                elif hasattr(module, 'handlers'):
                    for handler in module.handlers:
                        app.add_handler(handler)
                    loaded_count += 1
                    print(f"  ✅ {module_name}")
                else:
                    print(f"  ⚠️ {module_name} (нет register)")
                    
            except Exception as e:
                print(f"  ❌ {module_name}: {e}")
    
    print("="*50)
    log_bot_event(f"📦 Загружено команд: {loaded_count}")
    return loaded_count