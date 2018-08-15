import sys
import os.path
import json
import csv
import requests
from dotenv import load_dotenv

load_dotenv()

CLEARBIT_URL = 'https://autocomplete.clearbit.com/v1/companies/suggest'
FULLCONTACT_URL = 'https://api.fullcontact.com/v2/company/search.json'


def results_formatted_str(results, name_key, domain_key):
	return '\n'.join([
		'{} ({})'.format(res[name_key], res[domain_key])
		for res in results
	])


def enrich_data(inputfile, outfile):
	try:
		with open(inputfile, 'r', encoding='utf-8-sig') as f:
			reader = csv.DictReader(f)
			rows = list(reader)
			company_search_names = [row['Name'] for row in rows]
			headers = list(rows[0].keys())
	except:
		raise Exception('Could not read CSV data')

	with open(outfile, 'w') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=headers)
		writer.writeheader()

		for name in company_search_names:
			clearbit_response = requests.get(CLEARBIT_URL, params={
				'query': name,
			})
			clearbit_results_str = results_formatted_str(
				clearbit_response.json(),
				'name',
				'domain',
			)

			fullcontact_response = requests.get(FULLCONTACT_URL, params={
				'companyName': name,
			}, headers={
				'Authorization': 'Bearer {}'.format(
					os.getenv('FULLCONTACT_API_KEY', ''),
				),
			})
			if fullcontact_response.status_code == 200:
				fullcontact_results_str = results_formatted_str(
					fullcontact_response.json(),
					'orgName',
					'lookupDomain',
				)
			else:
				fullcontact_results_str = ''

			writer.writerow({
				'Name': name,
				'Clearbit': clearbit_results_str,
				'FullContact': fullcontact_results_str,
			})


if __name__ == '__main__':
	input_arg = sys.argv[1]
	output_arg = sys.argv[2]

	input_path = os.path.abspath(input_arg)
	output_path = os.path.abspath(output_arg)

	enrich_data(input_path, output_path)
