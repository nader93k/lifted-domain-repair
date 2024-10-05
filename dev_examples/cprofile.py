def example():
    benchmark_path = Path('./input/benchmarks-G1')
    # log_folder = Path('./exp_logs/4 BFS mega-run')
    log_folder = Path('./exp_logs_debug')

    solve_instance(search_algorithm=AStar
              , benchmark_path=benchmark_path
              , log_folder=log_folder
              , log_interval=200
              , instance_id='blocks/pprobBLOCKS-5-0-err-rate-0-5')

    cProfile.run("experiment(benchmark_path)", 'profiler_tmp')

def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)