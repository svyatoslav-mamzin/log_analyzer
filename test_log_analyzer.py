import unittest
import os

import log_analyzer as la


class LogAnalyzerTest(unittest.TestCase):

    def setUp(self):
        self.default_config = la.get_config()

    def test_load_config_from_args(self):
        self.assertTrue(
            la.load_config_from_args('config.json')
        )

    def test_get_last_file(self):
        self.assertEqual(
            la.get_last_file(self.default_config),
            'nginx-access-ui.log-20210630'
        )

    def test_analize_log_file(self):
        log_line1 = ['1.126.153.80 -  - [29/Jun/2017:04:46:00 +0300] ' \
                   '"GET /agency/outgoings_stats/?date1=28-06-2017&' \
                   'date2=28-06-2017&date_type=day&do=1&rt=banner&' \
                   'oi=25754435&as_json=1 HTTP/1.1" 200 217 "-" "-" "-" ' \
                   '"1498700760-48424485-4709-9957635" "1835ae0f17f" 0.068',

                     '1.202.56.176 -  - [29/Jun/2017:03:59:15 +0300] "0" ' \
                     '400 166 "-" "-" "-" "-" "-" 0.000'
                     ]
        self.default_config["REPORT_SIZE"] = 0
        self.assertEqual(
            la.analize_log_file(log_line1, self.default_config),
            [{'url': '/agency/outgoings_stats/?date1=28-06-2017&date2=28-06-2017&date_type=day&do=1&rt=banner&oi'
                     '=25754435&as_json=1', 'time_sum': 0.068, 'count': 1, 'count_perc': 50.0, 'time_perc': 100.0,
              'time_avg': 0.068, 'time_max': 0.068, 'time_med': 0.068},
             {'url': '0', 'time_sum': 0.0, 'count': 1, 'count_perc': 50.0, 'time_perc': 0.0, 'time_avg': 0.0,
              'time_max': 0.0, 'time_med': 0.0}]
        )

    def test_save_report_to_file(self):
        result = [{'url': '/agency/outgoings_stats/?date1=28-06-2017&date2=28-06-2017&date_type=day&do=1&rt=banner&oi'
                     '=25754435&as_json=1', 'time_sum': 0.068, 'count': 1, 'count_perc': 50.0, 'time_perc': 100.0,
              'time_avg': 0.068, 'time_max': 0.068, 'time_med': 0.068},
             {'url': '0', 'time_sum': 0.0, 'count': 1, 'count_perc': 50.0, 'time_perc': 0.0, 'time_avg': 0.0,
              'time_max': 0.0, 'time_med': 0.0}]
        self.assertEqual(la.save_report_to_file(result, self.default_config), './reports/report-{}.html')

        self.assertTrue(os.path.exists(la.save_report_to_file(result, self.default_config)))


if __name__ == '__main__':
    unittest.main()