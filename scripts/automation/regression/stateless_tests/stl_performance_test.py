import os
from .stl_general_test import CStlGeneral_Test, CTRexScenario
from common.performance_common import PerformanceReport
from trex_stl_lib.api import *
import pprint

def avg (values):
    return (sum(values) / float(len(values)))

class STLPerformance_Test(CStlGeneral_Test):
    """Tests for stateless client"""

    def setUp(self):

        CStlGeneral_Test.setUp(self)

        self.c = CTRexScenario.stl_trex
        self.c.connect()
        self.c.reset()
        cur_dir = os.path.dirname(__file__)
        self.profiles_dir = os.path.join(cur_dir, 'profiles')


    def tearDown (self):
        CStlGeneral_Test.tearDown(self)


    def build_perf_profile_vm (self, pkt_size, cache_size = None):
        f = os.path.join(self.profiles_dir, 'vm.py')
        p = STLProfile().load(f, pkt_size = pkt_size, cache_size = cache_size)
        return p.get_streams()


    def build_perf_profile_syn_attack(self, pkt_size):
        f = os.path.join(self.profiles_dir, 'syn.py')
        p = STLProfile().load(f, pkt_size = pkt_size)
        return p.get_streams()


    # single CPU, VM, no cache, 64 bytes
    def test_performance_vm_single_cpu (self):
        setup_cfg = self.get_benchmark_param('cfg')
        scenario_cfg = {}

        scenario_cfg['name']        = "VM - 64 bytes, single CPU"
        scenario_cfg['streams']     = self.build_perf_profile_vm(64)
        scenario_cfg['core_count']  = 1

        scenario_cfg['mult']                 = setup_cfg['mult']
        scenario_cfg['mpps_per_core_golden'] = setup_cfg['mpps_per_core_golden'] 
        
        

        self.execute_single_scenario(scenario_cfg)


    # single CPU, VM, cached, 64 bytes
    def test_performance_vm_single_cpu_cached (self):
        setup_cfg = self.get_benchmark_param('cfg')
        scenario_cfg = {}

        scenario_cfg['name']        = "VM - 64 bytes, single CPU, cache size 1024"
        scenario_cfg['streams']     = self.build_perf_profile_vm(64, cache_size = 1024)
        scenario_cfg['core_count']  = 1

        scenario_cfg['mult']                 = setup_cfg['mult']
        scenario_cfg['mpps_per_core_golden'] = setup_cfg['mpps_per_core_golden']

        self.execute_single_scenario(scenario_cfg)


    # single CPU, syn attack, 64 bytes
    def test_performance_syn_attack_single_cpu (self):
        setup_cfg = self.get_benchmark_param('cfg')
        scenario_cfg = {}

        scenario_cfg['name']        = "syn attack - 64 bytes, single CPU"
        scenario_cfg['streams']     = self.build_perf_profile_syn_attack(64)
        scenario_cfg['core_count']  = 1

        scenario_cfg['mult']                 = setup_cfg['mult']
        scenario_cfg['mpps_per_core_golden'] = setup_cfg['mpps_per_core_golden']

        self.execute_single_scenario(scenario_cfg)


    # two CPUs, VM, no cache, 64 bytes
    def test_performance_vm_multi_cpus (self):
        setup_cfg = self.get_benchmark_param('cfg')
        scenario_cfg = {}

        scenario_cfg['name']        = "VM - 64 bytes, multi CPUs"
        scenario_cfg['streams']     = self.build_perf_profile_vm(64)

        scenario_cfg['core_count']           = setup_cfg['core_count']
        scenario_cfg['mult']                 = setup_cfg['mult']
        scenario_cfg['mpps_per_core_golden'] = setup_cfg['mpps_per_core_golden']

        self.execute_single_scenario(scenario_cfg)



    # multi CPUs, VM, cached, 64 bytes
    def test_performance_vm_multi_cpus_cached (self):
        setup_cfg = self.get_benchmark_param('cfg')
        scenario_cfg = {}

        scenario_cfg['name']        = "VM - 64 bytes, multi CPU, cache size 1024"
        scenario_cfg['streams']     = self.build_perf_profile_vm(64, cache_size = 1024)


        scenario_cfg['core_count']           = setup_cfg['core_count']
        scenario_cfg['mult']                 = setup_cfg['mult']
        scenario_cfg['mpps_per_core_golden'] = setup_cfg['mpps_per_core_golden']

        self.execute_single_scenario(scenario_cfg)


    # multi CPUs, syn attack, 64 bytes
    def test_performance_syn_attack_multi_cpus (self):
        setup_cfg = self.get_benchmark_param('cfg')
        scenario_cfg = {}

        scenario_cfg['name']        = "syn attack - 64 bytes, multi CPUs"
        scenario_cfg['streams']     = self.build_perf_profile_syn_attack(64)

        scenario_cfg['core_count']           = setup_cfg['core_count']
        scenario_cfg['mult']                 = setup_cfg['mult']
        scenario_cfg['mpps_per_core_golden'] = setup_cfg['mpps_per_core_golden']

        self.execute_single_scenario(scenario_cfg)



############################################# test's infra functions ###########################################

    def execute_single_scenario (self, scenario_cfg):
        golden = scenario_cfg['mpps_per_core_golden']

        report = self.execute_single_scenario_iteration(scenario_cfg)

        if self.GAManager:
            report.report_to_analytics(self.GAManager, golden)

        #report to elk
        if self.elk:
            elk_obj = self.get_elk_obj()
            report.report_to_elk(self.elk,elk_obj)

        rc = report.check_golden(golden)

        if rc == PerformanceReport.GOLDEN_NORMAL or rc == PerformanceReport.GOLDEN_BETTER:
            return

        print("\n*** Measured Mpps per core '{0}' is lower than expected golden '{1}'".format(report.avg_mpps_per_core, scenario_cfg['mpps_per_core_golden']))

        assert 0, "performance failure"




    def execute_single_scenario_iteration (self, scenario_cfg):

        print("\nExecuting performance scenario: '{0}'\n".format(scenario_cfg['name']))

        self.c.reset(ports = [0])
        self.c.add_streams(ports = [0], streams = scenario_cfg['streams'])

        # use one core
        cores_per_port = self.c.system_info.get('dp_core_count_per_port', 0)
        if cores_per_port < scenario_cfg['core_count']:
            assert 0, "test configuration requires {0} cores but only {1} per port are available".format(scenario_cfg['core_count'], cores_per_port)

        core_mask = (2 ** scenario_cfg['core_count']) - 1
        self.c.start(ports = [0], mult = scenario_cfg['mult'], core_mask = [core_mask])

        # stablize
        print("Step 1 - waiting for stabilization... (10 seconds)")
        for _ in range(10):
            time.sleep(1)
            sys.stdout.write('.')
            sys.stdout.flush()

        print("\n")

        samples = {'cpu' : [], 'bps': [], 'pps': []}

        # let the server gather samples
        print("Step 2 - Waiting for samples... (60 seconds)")

        for i in range(0, 3):

            # sample bps/pps
            for _ in range(0, 20):
                stats = self.c.get_stats(ports = 0)
                max_queue_full = 100000 if self.is_VM else 10000 
                if stats['global'][ 'queue_full'] > max_queue_full:
                    assert 0, "Queue is full need to tune the multiplier"

                    # CPU results are not valid cannot use them 
                samples['bps'].append(stats[0]['tx_bps'])
                samples['pps'].append(stats[0]['tx_pps'])
                time.sleep(1)
                sys.stdout.write('.')
                sys.stdout.flush()

            # sample CPU per core
            rc = self.c._transmit('get_utilization')
            if not rc:
                raise Exception(rc)

            data = rc.data()['cpu']
            # filter
            data = [s for s in data if s['ports'][0] == 0]

            assert len(data) == scenario_cfg['core_count'] , "sampling info does not match core count"

            for s in data:
                samples['cpu'] += s['history']
            

        stats = self.c.get_stats(ports = 0)
        self.c.stop(ports = [0])


        
        avg_values = {k:avg(v) for k, v in samples.items()}
        avg_cpu  = avg_values['cpu'] * scenario_cfg['core_count']
        avg_gbps = avg_values['bps'] / 1e9
        avg_mpps = avg_values['pps'] / 1e6

        avg_gbps_per_core = avg_gbps * (100.0 / avg_cpu)
        avg_mpps_per_core = avg_mpps * (100.0 / avg_cpu)

        report = PerformanceReport(scenario            =  scenario_cfg['name'],
                                   machine_name        =  CTRexScenario.setup_name,
                                   core_count          =  scenario_cfg['core_count'],
                                   avg_cpu             =  avg_cpu,
                                   avg_gbps            =  avg_gbps,
                                   avg_mpps            =  avg_mpps,
                                   avg_gbps_per_core   =  avg_gbps_per_core,
                                   avg_mpps_per_core   =  avg_mpps_per_core)


        report.show()

        print("")
        golden = scenario_cfg['mpps_per_core_golden']
        print("golden Mpps per core (at 100% CPU):      min: {0}, max {1}".format(golden['min'], golden['max']))
        

        return report

