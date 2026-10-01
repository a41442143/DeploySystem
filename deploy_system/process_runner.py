from .models.result_model import ProcessResult , externalResult
import time
import subprocess
class process_runner:
    def __init__(self):
        pass
    def run(self,args,timeout, cwd= None):
        start_time =time.perf_counter()
        try:
            res = subprocess.run(
                args,
                capture_output=True,        #將結果存入result
                text=True,          #自動解碼成str
                timeout=timeout,     #指定逾時時間
                cwd =cwd        #指定工作資料夾
            )
            duration = time.perf_counter() - start_time
            
        except subprocess.TimeoutExpired as e:
        # time out 
            duration = time.perf_counter() - start_time
            process_result = ProcessResult(
                result = None,
                stdout = None,
                stderr =  str(e),
                time = duration , 
                error_code = 2
            )
            return process_result

        except OSError as e: 
        #子程序啟動失敗
            duration = time.perf_counter() - start_time
            process_result = ProcessResult(
                result = None,
                stdout = None,
                stderr =  str(e),
                time = duration,
                error_code = 1
            )
            return process_result
        else:
            process_result = ProcessResult(
                result = res.returncode,
                stdout = res.stdout ,
                stderr = res.stderr ,
                time = duration
            )
            return process_result
        
