from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.



@csrf_exempt 
def submit(request):
	print(request.method)	

	if request.method == "POST": 
		source_val = request.POST.get("id", "pye")
		return JsonResponse({'success':source_val})  
	else:
		source_val = request.GET.get("id","pye")
		return JsonResponse({'source_val':source_val})  


@csrf_exempt 
def themes(request):
	print(request.method)	

	if request.method == "POST": 
		source_val = request.POST.get("id", "pye")
		return JsonResponse({'success':source_val})  
	else:
		source_val = request.GET.get("id","pye")
		default_themes = [
		{"image":"https://th.bing.com/th/id/OIP.HxV79tFMPfBAIo0BBF-sOgHaEy?rs=1&pid=ImgDetMain","name":"Image 1"},
		{"image":"https://th.bing.com/th/id/R.7383028831604862ec47fefee3e8f43f?rik=JvqjDCfPocchLg&riu=http%3a%2f%2fthewowstyle.com%2fwp-content%2fuploads%2f2015%2f01%2fimages-of-nature-4.jpg&ehk=%2b1REJDS0cEPD0z2IP%2fddCyP9IgFz6xVpp8fyQr78SJ0%3d&risl=&pid=ImgRaw&r=0","name":"Image 2"},
		{"image":"https://th.bing.com/th/id/OIP.wwxK07x0Umfnh0l-nrjxjgHaDg?rs=1&pid=ImgDetMain","name":"Image 3"},
		{"image":"https://th.bing.com/th/id/R.f08b10ed58999a5a3ddfa4b88c65f0ac?rik=7hxMUDs5Zhk%2fng&pid=ImgRaw&r=0","name":"Image 4"},
		{"image":"https://th.bing.com/th/id/OIP.qDvAlhidTBzXiGyDfq_O0gHaE7?rs=1&pid=ImgDetMain","name":"Image 5"},

		]
		return JsonResponse(default_themes,safe=False)  
	

	

@csrf_exempt 
def select_theme(request):
	print(request.method)	

	if request.method == "POST": 
		source_val = request.POST.get("id", "pye")
		return JsonResponse({'success':source_val})  
	else:
		source_val = request.GET.get("id","pye")
		return JsonResponse({'source_val':source_val})  
	
	

@csrf_exempt 
def training_data(request):
	print(request.POST)	

	if request.method == "POST": 
		source_val = request.POST.get("id", "pye")
		return JsonResponse({'success':True})  
	else:
		source_val = request.GET.get("id","pye")
		return JsonResponse({'source_val':source_val})  
		

@csrf_exempt 
def training_status(request):
	source_val = request.GET.get("id","pye")
	return JsonResponse({'complete':True})  
	