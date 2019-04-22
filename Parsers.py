import Gadgets_PSASP
import const
import math
import re
import os


def parse_lines_PSASP(lines, pos_keys, dict_translate=const.dict_translate_lf,
                      pattern_parse=const.Pattern_read, multi_line=1, key_busno=None):
    lines_t = lines.copy()
    if str.find(lines_t[0], 'Created on') != -1:
        list.pop(lines_t, 0)

    if multi_line > 1:
        num_lines = len(lines_t)
        Ndiv = math.ceil(num_lines / multi_line)
        lines_t = [''.join([lines_t[hh] for hh in range(h * multi_line, (h + 1) * multi_line)]) for h in range(Ndiv)]

    list_dict_parsed = []
    append_no = isinstance(key_busno, str)
    for h in range(len(lines_t)):
        line_t = lines_t[h]
        if isinstance(line_t, str):
            contents = re.findall(pattern_parse, line_t)
            if contents:
                dict_t = {}
                for hh in range(min([len(contents), len(pos_keys)])):
                    key_t = pos_keys[hh]
                    trans_func_t = dict_translate[key_t]
                    if trans_func_t:
                        vt = trans_func_t(contents[hh])
                    else:
                        vt = contents[hh]
                    dict_t[key_t] = vt
                if append_no:
                    dict_t[key_busno] = h + 1
                list_dict_parsed.append(dict_t)

    return list_dict_parsed


def parse_lf(path_lf, pos_keys):
    suppath_t, lf_t = os.path.split(path_lf)
    if os.path.isfile(path_lf):
        with open(path_lf, 'r') as f:
            lines_raw = f.readlines()
        lines = [x.strip() for x in lines_raw]
        if lines:
            if lf_t in const.dict_multiline_lf.keys():
                multi_line = const.dict_multiline_lf[lf_t]
            else:
                multi_line = 1
            if lf_t in const.files_lf_append_no:
                key_busno = const.BusNoKey
            else:
                key_busno = None

            list_dict_parsed = parse_lines_PSASP(lines, pos_keys, multi_line=multi_line, key_busno=key_busno)
            return list_dict_parsed
    else:
        return None


def parse_all_files(path_temp, dict_files, dict_pos_keys, labels_do=None):
    labels_do_ori = list(dict_files.keys())
    flag_single = False
    if labels_do is not None:
        if isinstance(labels_do, str):
            flag_single = True
            labels_do = [labels_do]
        labels_do = set(labels_do_ori).intersection(set(labels_do))
    else:
        labels_do = labels_do_ori
    dict_r = {k: parse_lf(os.path.join(path_temp, dict_files[k]), dict_pos_keys[k]) for k in labels_do}
    if flag_single and len(dict_r) == 1:
        dict_r = list(dict_r.values())[0]
    return dict_r


def parse_all_files_s(path_temp, label_calType, label_getType, labels_do=None):
    dict_files = const.dict_mapping_files[label_calType][label_getType]
    dict_pos_keys = const.dict_mapping_pos_keys[label_calType][label_getType]
    dict_r = parse_all_files(path_temp, dict_files, dict_pos_keys, labels_do)
    return dict_r


def parse_all_settings_lf(path_temp, labels_do=None):
    return parse_all_files_s(path_temp, const.LABEL_LF, const.LABEL_SETTINGS, labels_do)


def parse_all_results_lf(path_temp, labels_do=None):
    return parse_all_files_s(path_temp, const.LABEL_LF, const.LABEL_RESULTS, labels_do)

def parse_all_settings_st(path_temp, labels_do=None):
    return parse_all_files_s(path_temp, const.LABEL_ST, const.LABEL_SETTINGS, labels_do)


if __name__ == '__main__':
    path_t = r'E:\01_Research\98_Data\华中电网大数据\华中2016夏（故障卡汇总）\Temp'
    # b = parse_all_results_lf(path_t, const.LABEL_BUS)
    # path_t = r'E:\01_Research\98_Data\SmallSystem_PSASP\Temp_LF+ST_SmallSystem_DoubleLine_backup_temp'
    settings_st = parse_all_settings_st(path_t)
    dt_r = parse_all_results_lf(path_t)
    dt = parse_all_settings_lf(path_t)
    print(dt)
