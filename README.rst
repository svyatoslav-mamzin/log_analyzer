Log Analyzer
============

Запуск скрипта:
---------------

* конфигурация по умолчанию

    :code:`python log_analyzer.py`

* использование конфигурации из файла config_file.py

    :code:`python log_analyzer.py --config config_file.json`

* использование конфигурации из директории ./CONFIG_DIR/, с именем config.json по умолчанию
  
    :code:`python log_analyzer.py --config ./CONFIG_DIR/`

* использование конфигурации config.json из директории ./CONFIG_DIR/

     :code:`python log_analyzer.py --config ./CONFIG_DIR/config.json`


Файл конфигурации может содержать частичную информацию, т.е хранить изменения только необходимых параметров.


Тестирование
------------

    :code:`python test_log_analyzer.py -v`
