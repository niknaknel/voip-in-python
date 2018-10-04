
def get_times(file_path):
    times = []
    with open(file_path, 'r+') as fp:
        line = fp.readline()
        while line:
            times.append(float(line))
            line = fp.readline()
    return times

if __name__=="__main__":
    starts = get_times("send.out")
    stops = get_times("recv.out")
    n = len(starts)

    diff = [stops[i] - starts[i] for i in range(n)]

    for d in diff:
        print d
