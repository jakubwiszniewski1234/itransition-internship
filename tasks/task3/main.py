import math
from flask import Flask, request

app = Flask(__name__)

def find_lowest_common_multiple(x, y):
    if x is None or y is None:
        return "NaN"
        
    try:
        str_x = str(x).strip()
        str_y = str(y).strip()
        if not str_x.isdigit() or not str_y.isdigit():
            return "NaN"
            
        ix = int(str_x)
        iy = int(str_y)
        if ix < 0 or iy < 0:
            return "NaN"
        return math.lcm(ix, iy)
        
    except (TypeError, ValueError, OverflowError):
        return "NaN"


@app.route('/jakubwiszniewski1234_gmail_com')
def handle_submission():
    x_param = request.args.get("x")
    y_param = request.args.get("y")
    
    result = str(find_lowest_common_multiple(x_param, y_param))
    return result.strip(), 200, {"Content-Type": "text/plain; charset=utf-8"}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)