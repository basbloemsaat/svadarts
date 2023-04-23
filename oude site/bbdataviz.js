// requires d3

var bbdataviz = {};
(function() {

    this.parameters = {
        row_height: 20,
        row_offset: 25,
        column_spacer: 25,
    }

    this.url_params = function() {
        var url = window.location.href;
        let url_params = {};
        var hashes = url.split("?")[1];
        if (hashes) {
            var hash = hashes.split('&');

            for (var i = 0; i < hash.length; i++) {
                let params = hash[i].split("=");
                url_params[params[0]] = params[1];
            }
        }

        return url_params;
    }


   

    this.xyChart = function(svg) {
        this.parameters = {
            "margin_left": 40,
            "margin_top": 5,
            "margin_right": 15,
            "margin_bottom": 25,
        };

        this.svg = svg;

        this.g = svg.append('g');
        this.content = this.g.append('g').classed('content', true);
        this.x_axis = this.g.append('g').classed('xaxis', true);
        this.y_axis = this.g.append('g').classed('yaxis', true);

        this.resize();
    }

    this.xyChart.prototype.resize = function() {
        let size = this.svg.node().getBoundingClientRect();
        let width = Math.floor(size.width);
        let height = Math.floor(size.height);

        this.content.attr('transform', 'translate('+this.parameters['margin_left']+','+this.parameters['margin_top']+')')
        this.c_width = width - this.parameters['margin_left'] - this.parameters['margin_right']
        this.c_height = height - this.parameters['margin_top'] - this.parameters['margin_bottom']
        this.x_axis.attr('transform', 'translate(' + this.parameters['margin_left'] + ',' + (height - this.parameters['margin_bottom']) + ')')
        this.y_axis.attr('transform', 'translate('+this.parameters['margin_left']+','+this.parameters['margin_top']+')')
    }

}).apply(bbdataviz);