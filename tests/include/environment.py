# tests/include/environment.py
from core.listener_manager import enabled_listeners

def before_feature(context, feature):
    for func in enabled_listeners['before_feature']:
        func(context, feature)

def after_feature(context, feature):
    for func in enabled_listeners['after_feature']:
        func(context, feature)

def before_scenario(context, scenario):
    for func in enabled_listeners['before_scenario']:
        func(context, scenario)

def after_scenario(context, scenario):
    for func in enabled_listeners['after_scenario']:
        func(context, scenario)
