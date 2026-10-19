require 'json'
weird_json = File.read('task1_d.json')
ruby_objects = eval(weird_json)
File.write('task3.5.json', JSON.pretty_generate(ruby_objects))