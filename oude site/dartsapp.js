var dartsapp = {};
(function() {

    this.data = {
        'index': {
            'spelers': [],
            'competitions': [],
        },
        'games': [],
        'spelers': {},
        'competitions': {},
    };

    this.root = './';

    this.loaded = {
        'index': false,
    }

    this.available_data = {
        'index': {}
    }

    this.load_data = function(callback, to_load = {}) {

        // function die checkt of alles geladen is. Als alles is geladen wordt
        // de callback aangeroepen, anders return zonder actie
        let collector = function() {
            // todo: check of alles geladen is. Nu laden we nog maar één ding,
            // dus yagni
            callback();
        }

        for (let i in to_load) {
            if (i == 'index') {
                d3.json(this.root + 'data/index.json')
                    .then(
                        function(data) {
                            dartsapp.data['index'] = data;
                            dartsapp.loaded['index'] = true;
                            collector();
                        }
                    )
            } else if (i == 'spelers') {
                for (let s in to_load[i]) {
                    d3.json(this.root + 'data/perspeler/' + to_load[i][s] + '.json')
                        .then(
                            function(data) {
                                let seasons = {};
                                dartsapp.data['spelers'][to_load[i][s]] = data;
                                let games = data.games;
                                games.sort(function(a, b) {
                                    return a.game_order - b.game_order
                                })
                                let avonden = data.avonden;

                                avonden.sort(function(a, b) {
                                    let ca = a.datum.replace(/-/g, '')
                                    let cb = b.datum.replace(/-/g, '')
                                    return ca - cb
                                })

                                for (let g in games) {
                                    let game = games[g];
                                    game['date'] = new Date(game['datum'] + ' 12:00');
                                }

                                for (let a in avonden) {
                                    let avond = avonden[a];
                                    let c = avond['comp']

                                    if (!Object.keys(seasons).includes(c)) {
                                        seasons[c] = 0
                                    }

                                    seasons[c] += avond.punten;
                                    avond['comp_punten'] = seasons[c];

                                    avond['date'] = new Date(avond['datum'] + ' 12:00');
                                    avond['timestamp'] = Date.parse(avond['datum'] + ' 12:00');
                                }

                                collector();
                            }
                        )
                }
            } else if (i == 'seizoenen') {
                for (let s in to_load[i]) {
                    d3.json(this.root + 'data/perseason/' + to_load[i][s] + '.json')
                        .then(function(data) {
                                dartsapp.data['competitions'][to_load[i][s]] = data;
                                collector();
                            }

                        )
                }

            } else {
                console.log(i)
            }
        }
    }
}).apply(dartsapp);