import os
# Disable future warnings.
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import matplotlib
# Disable interactive GUI plotting.
matplotlib.use('Agg')
import pandas as pd
from django.http import FileResponse, Http404
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import FileUploadForm
import numpy as np
np.float_ = np.float64
from prophet import Prophet
import io
import base64
import urllib.parse


def upload_file(request):
    if request.method == 'POST':

        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():

            # Add a message to indicate the model is being trained.
            messages.success(request, 'Upload another dataset to view more predictions.')
            
            # Save the uploaded file.
            form.save()
            
            # Data pre-processing.
            file = request.FILES['file']
            # Load the Excel file into Pandas.
            df = pd.read_excel(file, skiprows=2)
            # Convert "Date" attribute to datetime format.
            df['ds'] = pd.to_datetime(df['Date'])
            # Drop unnecessary columns.
            df = df.drop(columns=['Date', 'Total', 'Last Updated', 'UpdatedBy', 'Comment'], errors='ignore')
            # Rename columns for target variables.
            target_variables = ['O Pos', 'O Neg', 'A Pos', 'A Neg', 'B Pos', 'B Neg', 'AB Pos', 'AB Neg']

            # Create dictionaries to store the models and forecasts.
            models = {}
            forecasts = {}
            plots = {}

            # Loop over each target variable.
            for target in target_variables:
                if target in df.columns:
                    print(f"Training model for {target}...")
                    df_target = df[['ds', target]].rename(columns={target: 'y'})
                    
                    # Create and train the model.
                    model = Prophet(interval_width=0.95, yearly_seasonality=10)
                    model.fit(df_target)

                    # Make predictions.
                    future = model.make_future_dataframe(periods=31)
                    forecast = model.predict(future)

                    # Store the model and forecast.
                    models[target] = model
                    forecasts[target] = forecast

                    # Plot the forecast.
                    fig = model.plot(forecast, figsize=(10, 6))
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png')
                    buf.seek(0)
                    string = base64.b64encode(buf.read())
                    uri = 'data:image/png;base64,' + urllib.parse.quote(string)
                    
                    plots[target] = uri

            # Save the plots URIs to session to pass to another view.
            request.session['plots'] = plots

            return render(request, 'forecast/predicted_results', {'plots': plots})

        else:
            return render(request, 'forecast/error.html', {'error': 'Invalid data format.'})

    else:
        form = FileUploadForm()
    
    return render(request, 'forecast/upload.html', {'form': form})


# View to display the plotted results.
def results(request):
    plots = request.session.get('plots', None)
    if not plots:
        return render(request, 'forecast/error.html', {'error': 'No predictions available. Please upload a dataset first.'})

    return render(request, 'forecast/predicted_results', {'plots': plots})


def predefined_file_list(request):
    # Defined path to static files directory.
    files_dir = os.path.join(settings.BASE_DIR, 'forecast/static/files')
    
    # List all files in the static files directory.
    try:
        files = os.listdir(files_dir)
    except FileNotFoundError:
        files = []

    return render(request, 'forecast/predefined_files.html', {'files': files})


def download_predefined_file(request, filename):
    file_path = os.path.join(settings.BASE_DIR, 'forecast/static/files', filename)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    else:
        raise Http404("File not found.")
    

def notifications(request):
    return render(request, 'forecast/notifications.html')


def predicted_demand(request):
    return render(request, 'forecast/predicted_demand.html')


def login_user(request):
	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			messages.success(request, ("Login successful"))
			return redirect('upload_file')
		else:
			messages.success(request, ("Login unsuccessful"))
			return redirect('login')

	else:
		return render(request, 'forecast/upload.html', {})
     

def logout_user(request):
	logout(request)
	messages.success(request, ("Logout successful"))
	return redirect('login')

