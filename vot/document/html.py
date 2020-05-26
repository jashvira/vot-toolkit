
import os
import io
import logging
import datetime
from typing import List

import dominate
from dominate.tags import h1, h2, table, thead, tbody, tr, th, td, div, p, li, ol, span, style, link, script
from dominate.util import raw

from vot import toolkit_version, check_debug
from vot.tracker import Tracker
from vot.dataset import Sequence
from vot.workspace import Storage
from vot.document.common import format_value, read_resource, merge_repeats, extract_measures_table, extract_plots
from vot.document import StyleManager

def generate_html_document(trackers: List[Tracker], sequences: List[Sequence], results, storage: Storage):

    order_classes = {1: "first", 2: "second", 3: "third"}

    def insert_figure(figure):
        buffer = io.StringIO()
        figure.save(buffer, "SVG")
        raw(buffer.getvalue())

    def insert_cell(value, order):
        attrs = dict(data_sort_value=order, data_value=value)
        if order in order_classes:
            attrs["cls"] = order_classes[order]
        td(format_value(value), **attrs)

    def add_style(name, linked=False):
        if linked:
            link(rel='stylesheet', href='file://' + os.path.join(os.path.dirname(__file__), name))
        else:
            style(read_resource(name))

    def add_script(name, linked=False):
        if linked:
            script(type='text/javascript', src='file://' + os.path.join(os.path.dirname(__file__), name))
        else:
            with script(type='text/javascript'):
                raw("//<![CDATA[\n" + read_resource(name) + "\n//]]>")

    logger = logging.getLogger("vot")

    table_header, table_data, table_order = extract_measures_table(trackers, results)
    plots = extract_plots(trackers, results)

    legend = StyleManager.default().legend(Tracker)

    doc = dominate.document(title='VOT report')

    linked = check_debug()

    with doc.head:
        add_style("pure.css", linked)
        add_style("report.css", linked)
        add_script("jquery.js", linked)
        add_script("table.js", linked)
        add_script("report.js", linked)

    with doc:

        h1("VOT report")

        with ol(cls="metadata"):
            li('Toolkit version: ' + toolkit_version())
            li('Created: ' + datetime.datetime.now().isoformat())

        if len(table_header[2]) == 0:
            logger.debug("No measures found, skipping table")
        else:
            with table(cls="measures pure-table pure-table-horizontal pure-table-striped"):
                with thead():
                    with tr():
                        th()
                        [th(c[0].identifier, colspan=c[1]) for c in merge_repeats(table_header[0])]
                    with tr():
                        th()
                        [th(c[0].title, colspan=c[1]) for c in merge_repeats(table_header[1])]
                    with tr():
                        th("Trackers")
                        [th(c.abbreviation, data_sort="int" if order else "") for c, order in zip(table_header[2], table_order)]
                with tbody():
                    for tracker, data in table_data.items():
                        with tr():
                            number = legend.number(tracker.identifier)
                            with td(id="legend_%d" % number):
                                insert_figure(legend.figure(tracker.identifier))
                                span(tracker.label)
                            for value, order in zip(data, table_order):
                                insert_cell(value, order[tracker] if not order is None else None)

        for experiment, experiment_plots in plots.items():
            if len(experiment_plots) == 0:
                continue

            h2("Experiment {}".format(experiment.identifier), cls="experiment")

            with div(cls="plots"):

                for title, plot in experiment_plots:
                    with div(cls="plot"):
                        p(title)
                        insert_figure(plot)
                        

    with storage.write("report.html") as filehandle:
        filehandle.write(doc.render())