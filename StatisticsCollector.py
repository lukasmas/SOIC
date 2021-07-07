from dataclasses import dataclass


@dataclass
class DamageStatistics:
    total_sent: int = 0
    damaged: int = 0


@dataclass
class SentStatistics:
    sent: int = 0
    forwarded: int = 0
    broadcast: int = 0


@dataclass
class PathLength:
    destination: int = 0
    length: int = 0


@dataclass
class Statistics:
    damage_statistics: DamageStatistics = DamageStatistics()
    sent_statistics: SentStatistics = SentStatistics()
    path_length: list[PathLength] = list[PathLength()]


class StatisticsCollector:
    def __init__(self, queue):
        self.statistics = dict()
        self.stats_queue = queue
        # self.test = statistics

    def update_stats(self):
        while not self.stats_queue.empty():
            stat = self.stats_queue.get()
            node_stat = self.statistics.get(stat[0])
            if type(stat[1]) is DamageStatistics:
                node_stat.damage_statistics = stat[1]
            if type(stat[1]) is SentStatistics:
                node_stat.sent_statistics = stat[1]

    def add_stats(self, node_id):
        if node_id not in self.statistics.keys():
            self.statistics[node_id] = Statistics(DamageStatistics(0, 0), SentStatistics(0, 0, 0), PathLength(0, 0))

    def print_stats(self):
        for s in self.statistics:
            print()
            print(f'{s}: {self.statistics.get(s).damage_statistics}')
            print(f'{s}: {self.statistics.get(s).sent_statistics}')


#komunikacja bezprzewodowa
#narysować graf połączeń

#algorytm z literatury

#next week algorytm do balansowania ruchu

#czysczenie wag
#reinicjalizacja wag

