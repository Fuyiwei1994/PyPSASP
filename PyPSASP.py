import os
import Gadgets_PSASP
import const
from Executors import executor_PSASP_lf, executor_PSASP_st
import Gadgets_sqlite
import Gadgets
from Parsers import PSASP_Parser
import random

PATH_TEMP = r'E:\01_Research\98_Data\SmallSystem_PSASP\Temp_20190419'
PATH_RESOURCES = r'E:\05_Resources\Softwares\PSASP\CriticalFiles_60000'
PATH_OUTPUT = r'F:\Data\Research\PyPSASP\CCT\3m'


def func_change_lf_temp(P):
    if isinstance(P, PSASP):
        gen_ori = P.parser.parse_single_s_lfs(const.LABEL_GENERATOR)
        load_ori = P.parser.parse_single_s_lfs(const.LABEL_LOAD)
        gen_new = gen_ori.copy()
        load_new = load_ori.copy()
        for hh in range(len(gen_new)):
            gen_new[hh][const.GenPgKey] = gen_new[hh][const.PmaxKey] * (random.random() * 0.5 + 0.5)
            gen_new[hh][const.GenQgKey] = gen_new[hh][const.QmaxKey] * (random.random() * 0.5 + 0.5)
            '''
            for key_t in [const.GenPgKey,const.GenQgKey,const.V0Key,const.AngleKey]:
                gen_new[hh][key_t] = gen_new[hh][key_t]*(random.random()*0.5+0.5)
            '''
        for hh in range(len(load_new)):
            load_new[hh][const.LoadPlKey] = load_new[hh][const.PmaxKey] * (random.random() * 0.5 + 0.5)
            load_new[hh][const.LoadQlKey] = load_new[hh][const.QmaxKey] * (random.random() * 0.5 + 0.5)
            '''
            for key_t in [const.LoadPlKey,const.LoadQlKey,const.V0Key,const.AngleKey]:
                load_new[hh][key_t] = load_new[hh][key_t]*(random.random()*0.5+0.5)
            '''

        P.parser.write_to_file_s_lfs_autofit(gen_new)
        P.parser.write_to_file_s_lfs_autofit(load_new)


def func_change_t_regular(P, t):
    if isinstance(P, PSASP):
        STS11_ori = P.parser.parse_single_s(const.LABEL_ST, const.LABEL_SETTINGS, const.LABEL_FAULT)
        STS11_new = STS11_ori.copy()
        STS11_new[0][const.FaultTstartKey] = 0
        STS11_new[1][const.FaultTstartKey] = t
        STS11_new[2][const.FaultTstartKey] = t + 0.01
        P.parser.write_to_file_s(const.LABEL_ST, const.LABEL_SETTINGS, const.LABEL_FAULT, STS11_new)


def func_judge_stable_regular(P):
    F = None
    if isinstance(P, PSASP):
        STCAL = P.parser.parse_single_s(const.LABEL_ST, const.LABEL_RESULTS, const.LABEL_CONF)
        F = STCAL[const.STIsStableKey] == 1
    return F


class PSASP(object):
    @property
    def path_temp(self):
        return self.__path_temp

    @property
    def path_resources(self):
        return self.__path_resources

    @path_temp.setter
    def path_temp(self, value):
        if not isinstance(value, str):
            raise ValueError('path_temp must be a string!')
        elif not os.path.isdir(value):
            os.makedirs(value)
        self.__path_temp = value
        self.parser = PSASP_Parser(value)

    @path_resources.setter
    def path_resources(self, value):
        if not isinstance(value, str):
            raise ValueError('path_resources must be a string!')
        elif not os.path.isdir(value):
            raise ValueError('path_resources should be an existing folder!')
        self.__path_resources = value
        self.__path_exe_wmlfmsg = os.path.join(self.__path_resources, const.EXE_LF)
        self.__path_exe_wmudrt = os.path.join(self.__path_resources, const.EXE_ST)
        self.__executor_lf = executor_PSASP_lf(self.__path_exe_wmlfmsg, self.path_temp)
        self.__executor_st = executor_PSASP_st(self.__path_exe_wmudrt, self.path_temp)

    def __init__(self, path_temp, path_resources):
        self.path_temp = path_temp
        self.path_resources = path_resources

    def calculate_LF(self):
        success_lf = False
        self.__executor_lf.execute_exe()
        LFCAL = self.parser.parse_single_s(const.LABEL_LF, const.LABEL_RESULTS, const.LABEL_CONF)
        if LFCAL:
            if const.MCalKey in LFCAL.keys():
                success_lf = LFCAL[const.MCalKey] == 1
        return success_lf

    def calculate_CCT(self, path_save_left, path_save_right,
                      func_change_t=func_change_t_regular,
                      func_judge_stable=func_judge_stable_regular,
                      Tstep_max=0.2, label=None):

        if label is None:
            label = '-------AFFAIR-------'
        rec = {
            'Tmax': Tstep_max,
            'Tsim': 5,
            'eps': 0.001,
            'tleft': 0,
            'tright': Tstep_max,
            'CCT': float('nan'),
            'fleft': False,
            'fright': True,
            'count': 0,
            'flag_limit_touched': False,
            'output_st_left': path_save_left,
            'output_st_right': path_save_right
        }

        while abs(rec['tleft'] - rec['tright']) > rec['eps']:
            if rec['count'] == 0 or (not rec['flag_limit_touched']):
                CT_t = rec['tright']
            else:
                CT_t = (rec['tleft'] + rec['tright']) / 2
            func_change_t(self, CT_t)
            self.__executor_st.execute_exe()
            stable = func_judge_stable(self)
            if stable:
                rec['tleft'] = CT_t
                rec['fleft'] = stable
                rec['CCT'] = CT_t
                # TODO: Donnot copy?
                Gadgets_PSASP.copyfiles_st(self.path_temp, rec['output_st_left'])
                if not rec['flag_limit_touched']:
                    rec['tright'] = CT_t + Tstep_max

            else:
                rec['tright'] = CT_t
                rec['fright'] = stable
                # TODO: Donnot copy?
                Gadgets_PSASP.copyfiles_st(self.path_temp, rec['output_st_right'])
                rec['flag_limit_touched'] = True

            rec['count'] += 1
            print('%s%d (%d): %.4f, %.4f' % (label, rec['count'], stable, rec['tleft'], rec['tright']))
        print('%sCCT = %.4f' % (label, rec['CCT']))

        return rec


class CCT_generator(object):
    @property
    def path_output(self):
        return self.__path_output

    @path_output.setter
    def path_output(self, value):
        if not isinstance(value, str):
            raise ValueError('path_output should be string!')
        else:
            if not os.path.isdir(value):
                os.makedirs(value)
            self.__path_output = value
            self.__path_record_master = os.path.join(value, 'record.db')
            self.__path_output_st = os.path.join(value, const.LABEL_ST)
            self.__path_output_lf = os.path.join(value, const.LABEL_LF)
            self.__path_output_st_left = os.path.join(self.__path_output_st, 'left')
            self.__path_output_st_right = os.path.join(self.__path_output_st, 'right')

    def __init__(self, path_temp, path_resources, path_output, func_change_lfs):
        self.__path_temp = path_temp
        self.__PSASP = PSASP(path_temp, path_resources)
        self.path_output = path_output
        self.__func_change_lfs = func_change_lfs
        self.__name_gen_st_left = Gadgets.generate_new_files_save_yield(self.__path_output_st_left, 'left',
                                                                        flag_dir=True, return_path=True)
        self.__name_gen_st_right = Gadgets.generate_new_files_save_yield(self.__path_output_st_right, 'right',
                                                                         flag_dir=True, return_path=True)
        self.__name_gen_lf = Gadgets.generate_new_files_save_yield(self.__path_output_lf, const.LABEL_LF, flag_dir=True,
                                                                   return_path=True)

    def run_sim_CCT_once(self):
        self.__func_change_lfs(self.__PSASP)
        success_lf = self.__PSASP.calculate_LF()
        # success_lf = True
        rec_t = {'success_lf': success_lf}
        flft = next(self.__name_gen_lf)
        if success_lf:
            fstleftt = next(self.__name_gen_st_left)
            fstrightt = next(self.__name_gen_st_right)
            Gadgets_PSASP.copyfiles_lf(self.__path_temp, flft)
            rec_t['output_lf'] = flft
            rec_t_st = self.__PSASP.calculate_CCT(fstleftt, fstrightt)
            rec_t.update(rec_t_st)
        else:
            Gadgets_PSASP.copyfiles_lfs(self.__path_temp, flft)
            rec_t['output_lf'] = flft

        keys_t = list(rec_t.keys())
        values_t = list(rec_t.values())
        Gadgets_sqlite.insert_from_list_to_db(self.__path_record_master, 'records', keys_t, [values_t])


if __name__ == '__main__':
    os.system('@echo off')
    Cc = CCT_generator(PATH_TEMP, PATH_RESOURCES, PATH_OUTPUT, func_change_lf_temp)
    count_t = 0
    max_count = 10000
    while count_t <= max_count:
        Cc.run_sim_CCT_once()
        count_t += 1

    '''
    path_resources_t = r'E:\05_Resources\Softwares\PSASP\CriticalFiles_60000'
    path_temp_t = r'E:\01_Research\98_Data\SmallSystem_PSASP\Temp_20190419'
    path_save_left_t = r'E:\01_Research\98_Data\SmallSystem_PSASP\left'
    path_save_right_t = r'E:\01_Research\98_Data\SmallSystem_PSASP\right'
    PSASP_t = PSASP(path_temp_t,path_resources_t)
    rec_t = PSASP_t.calculate_CCT(path_save_left_t,path_save_right_t)
    print(rec_t)
    '''
