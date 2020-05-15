# Delivery Routes

Generate fixed sized groupings of destinations

## Installation

1. Get code

```bash
git clone https://github.com/driazati/route_generator.git
cd route_generator
pip3 install -r requirements.txt
```

2. Set up [Bing Maps API key](https://www.bingmapsportal.com/)

Create a file called `secret.py` and add the key:
```bash
echo "bing_api_key = '<YOUR API KEY>' > secret.py"
```

3. Add `.csv` file to the folder, name it `file.csv`

## Run

Basic usage

```bash
python3 main.py
```

Run and put the results into a file

```bash
python3 main.py > output.txt
```
