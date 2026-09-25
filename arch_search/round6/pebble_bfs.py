import sys, json, time
from pebble import from_xag, bfs
sol = json.load(open(sys.argv[1])); nanc = int(sys.argv[2]); cap = int(sys.argv[3]) if len(sys.argv) > 3 else 5_000_000
ro = list(map(int, sys.argv[4].split(','))) if len(sys.argv) > 4 and sys.argv[4] else []
game, V0 = from_xag(sol, nanc, ro); t0 = time.time()
path, n = bfs(game, V0, cap)
print(sys.argv[1], 'nanc', nanc, 'states', n, 'schedule', path, 'len', None if path is None else len(path), '%.0fs' % (time.time() - t0), flush=True)
