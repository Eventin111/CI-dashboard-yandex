# CI Health & Duration — Grafana

Локальный Grafana-дашборд по данным из `Данные для тестового.xlsx`.

## Запуск

1. Запустите Docker Desktop.
2. В этой папке выполните:

   ```bash
   docker compose up -d
   ```

3. Откройте [http://localhost:3000/d/ci-health-duration/ci-health-duration](http://localhost:3000/d/ci-health-duration/ci-health-duration).

Просмотр доступен без входа. Для редактирования используйте `admin` / `admin` и смените пароль при первом входе, если Grafana предложит.

## Что включено

- Success Rate по условным неделям;
- медиана Pipeline Duration с разложением на Queue и Execution;
- P90 длительности и доля очереди;
- ошибки по этапам как диагностический прокси;
- длительность по размеру изменения;
- таблица самых долгих запусков;
- фильтры по неделе, размеру изменения и статусу;
- явные data-gap панели для MTTR и падающих тестов.

`slowest_check_type` показывает самую долгую проверку, а не реальный этап падения. Поэтому панель ошибок помечена как прокси. В исходном XLSX нет названий отдельных тестов и времён инцидентов, необходимых для Top failing tests и MTTR.

## Обновление данных

После замены XLSX пересоберите SQL:

```bash
python3 ../scripts/read_xlsx.py '../Данные для тестового.xlsx' > /tmp/ci_workbook.jsonl
python3 ../scripts/export_ci_sql.py /tmp/ci_workbook.jsonl postgres/init.sql
```

Для повторной инициализации PostgreSQL потребуется удалить локальный volume и снова поднять стек.
