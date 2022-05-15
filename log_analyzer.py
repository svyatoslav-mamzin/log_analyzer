#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import gzip
import json
import logging
import argparse
from collections import namedtuple
from datetime import datetime
from statistics import median

NamedFileInfo = namedtuple('NamedFileInfo', ['log_name', 'date_log'])


def get_command_options():
    description = "Analyze nginx logfiles and create report."
    parser = argparse.ArgumentParser(description=description)
    help_description = 'Config file name or config directory by default name "config.json"'
    parser.add_argument('--config', nargs=1, metavar='config_file', help=help_description)
    return parser.parse_args()


def load_config_from_args(config_from_args):
    default_filename = 'config.json'

    if os.path.isfile(config_from_args):
        pathname = config_from_args
    elif os.path.isdir(config_from_args):
        pathname = os.path.join(config_from_args, default_filename)
    else:
        logging.error(f"Config file not found: {config_from_args}")
        return {}
    try:
        with open(pathname, 'rb') as conf_file:
            return json.load(conf_file)
    except:
        logging.error(f"Can't use config file: {config_from_args}")
        return {}


def get_config(*args):
    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
        "REPORT_TEMPLATE": "templates/report.html",
        "REPORT_NAME": "report-{}.html",
        "REGEXP_FIND_DATE_FROM_FILE_NAME": "^nginx-access-ui.log-([0-9]{8})",
        "LOG_OUTPUT_FILE": None,
        "LOG_FORMAT": '[%(asctime)s] %(levelname).1s %(message)s',
        "LOG_DATA_FORMAT": '%Y.%m.%d %H:%M:%S',
        "LOG_LEVEL": logging.INFO,
        "PARSER_REGEXP": "(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})([\s-]+).+"
                         + "(?P<date>\[[\/\w:\s+]+\])\s"
                         + "\"\w*\s*(?P<url>[\w\/\.\-?\&\%_=:]+).+"
                         + "\s(?P<request_time>[0-9\.]+)$",
        "PARSER_MAX_PERCENT_ERRORS": 75,
    }

    if hasattr(args, 'config') and args.config:
        config_from_file = load_config_from_args(args.config[0])
        if isinstance(config_from_file, dict):
            config = dict(config, **config_from_file)

    return config


def get_last_file(config):
    log_files = {}
    for file_in_dir in os.listdir(config['LOG_DIR']):
        result = re.search(config["REGEXP_FIND_DATE_FROM_FILE_NAME"], file_in_dir)
        if result:
            try:
                datetime_object = datetime.strptime(result.group(1), '%Y%m%d')
                log_files[datetime_object] = file_in_dir
            except ValueError:
                continue

    if not log_files:
        return None

    max_date_in_files = max(dt for dt in log_files.keys())
    return NamedFileInfo(log_name=log_files[max_date_in_files],
                         date_log=max_date_in_files.strftime("%Y.%m.%d"))


def open_log_file(log_dir, last_log_file):
    log_file = os.path.join(log_dir, last_log_file)
    try:
        return gzip.open(log_file, 'rb') if log_file.endswith(".gz") else open(log_file)
    except:
        logging.exception("Open file error")


def check_percent_errors(count_line, count_line_parse_errors, parser_max_percent_errors):
    current_percent_errors = int(float(count_line_parse_errors) * 100 / float(count_line))
    if current_percent_errors > parser_max_percent_errors:
        logging.error(f"Reached maximum number of parser errors ({count_line_parse_errors}"
                      f" from {count_line}) it's more then {parser_max_percent_errors}%")


def analize_log_file(fd_log, config):
    report_size = config['REPORT_SIZE']
    analize_result = {}
    count_all_reqest = 0
    count_all_request_time = 0
    count_line_parse_errors = 0
    ROUND_NUMBER = 3
    for log_line in fd_log:
        count_all_reqest += 1
        result = re.search(config['PARSER_REGEXP'], str(log_line))
        if result:
            url = result.group("url")
            key = url
            request_time = float(result.group("request_time"))
            count_all_request_time += request_time
            if analize_result.get(key):
                analize_result[key]['time_sum'] += request_time
                analize_result[key]['time_list'].append(request_time)
            else:
                analize_result[key] = {'url': url,
                                       'time_sum': request_time,
                                       'time_list': [request_time]}
        else:
            count_line_parse_errors += 1

    check_percent_errors(count_all_reqest, count_line_parse_errors, config['PARSER_MAX_PERCENT_ERRORS'])

    for key in list(analize_result):
        if analize_result[key]['time_sum'] < report_size:
            del analize_result[key]
            continue
        analize_result[key]['count'] = len(analize_result[key]['time_list'])
        analize_result[key]['count_perc'] = round((float(analize_result[key]['count'])) * 100 / float(count_all_reqest),
                                                  ROUND_NUMBER)
        analize_result[key]['time_perc'] = round(
            (float(analize_result[key]['time_sum'])) * 100 / float(count_all_request_time), ROUND_NUMBER)
        analize_result[key]['time_avg'] = round(analize_result[key]['time_sum'] / analize_result[key]['count'],
                                                ROUND_NUMBER)
        analize_result[key]['time_max'] = round(max(analize_result[key]['time_list']), ROUND_NUMBER)
        analize_result[key]['time_med'] = round(median(analize_result[key]['time_list']), ROUND_NUMBER)
        analize_result[key]['time_sum'] = round(analize_result[key]['time_sum'], ROUND_NUMBER)
        del analize_result[key]['time_list']

    return list(analize_result.values())


def save_report_to_file(result, date_log, config):
    report_name = config["REPORT_NAME"].format(date_log)
    if config.get('REPORT_DIR') and not os.path.isdir(config['REPORT_DIR']):
        os.mkdir(config['REPORT_DIR'])
    report_template = config['REPORT_TEMPLATE']
    report_result = os.path.join(config['REPORT_DIR'], report_name)
    try:
        with open(report_template, "rt") as fin:
            with open(report_result, "wt") as fout:
                for line in fin:
                    fout.write(line.replace('$table_json', json.dumps(result)))
        return report_result
    except:
        logging.exception("Save report error")
        os.remove(report_result)


def main():
    all_args = get_command_options()
    config = get_config(all_args)
    logging.basicConfig(filename=config["LOG_OUTPUT_FILE"],
                        format=config["LOG_FORMAT"],
                        datefmt=config["LOG_DATA_FORMAT"],
                        level=config['LOG_LEVEL'])
    try:
        last_log_file = get_last_file(config)
        if not last_log_file:
            logging.info("No file to analyze")
            return
        if os.path.exists(os.path.join(config['REPORT_DIR'], config['REPORT_NAME'].format(last_log_file.date_log))):
            logging.info(f"The report for {last_log_file.log_name} is ready.")
        else:
            fd_log = open_log_file(config['LOG_DIR'], last_log_file.log_name)
            logging.info(f"Start analysis log {last_log_file.log_name}")
            result = analize_log_file(fd_log, config)
            report_file = save_report_to_file(result, last_log_file.date_log, config)
            logging.info(f"End analysis and save report in {report_file}")
    except:
        logging.exception("We have a problem")


if __name__ == "__main__":
    main()
