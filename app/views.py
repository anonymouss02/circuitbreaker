from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from circuitbreaker import circuit
import requests

# Create your views here.

rc_code = {
    'ERR-UNDEFINED'                 :   '5',
    'ERR-METHOD-NOT-AVAILABLE'      :   '30',
    'ERR-EMPTY-REQUIRED-FIELD'      :   '30',
    'ERR-INVALID-NUMBER'            :   '30',
    'ERR-NOT-AN-OPERATOR'           :   '30',
    'ERR-SECURE-HASH'               :   '30',
    'ERR-BULK'                      :   '30',
    'ERR-RESPONSE-TIMEOUT'          :   '68',
    'ERR-DB'                        :   '91',
}

def fallbackFunction(args, kwrags) :
    return "Circuit Breaker sedang open."

@csrf_exempt
def init(request) :
    if request.method == 'POST' :
        action = request.POST['action']
        kodeBank = request.POST['kodeBank']
        kodeBiller = request.POST['kodeBiller']
        kodeChannel = request.POST['kodeChannel']
        kodeTerminal = request.POST['kodeTerminal']
        nomorPembayaran = request.POST['nomorPembayaran']
        tanggalTransaksi = request.POST['tanggalTransaksi']
        idTransaksi = request.POST['idTransaksi']
        checksum = request.POST['checksum']

        data = {'action': action,
            'kodeBank': kodeBank,
            'kodeBiller': kodeBiller,
            'kodeChannel': kodeChannel,
            'kodeTerminal': kodeTerminal,
            'nomorPembayaran': nomorPembayaran,
            'tanggalTransaksi': tanggalTransaksi,
            'idTransaksi': idTransaksi,
            'checksum': checksum}

        data2 = {'kd_term': kodeTerminal,
            'kd_org': kodeBiller,
            'no_pokok': nomorPembayaran,
            'year': tanggalTransaksi[:4],
            'month': tanggalTransaksi[4:6],
            'day': tanggalTransaksi[6:8],
            'hour': tanggalTransaksi[8:10]}

        if (action == 'inquiry') :
            r = requests.post(url="http://localhost:8002", data=data).json()
            print(r['rc'])

            if (r['rc'] in rc_code) :
                kode = rc_code[r['rc']]
                data2['rc'] = 'INQ-' + kode
                
                try :
                    r2 = circuit_breaker("http://localhost:8000/predict/", data2)
                except IOError:
                    return JsonResponse(r)
                else:
                    if r2 == 'Circuit Breaker sedang open.' :
                        return HttpResponse("Circuit Breaker sedang open.")

        elif (action == 'payment') :
            idTagihan = request.POST['idTagihan']
            totalNominal = request.POST['totalNominal']
            nomorJurnalPembukuan = request.POST['nomorJurnalPembukuan']

            data['idTagihan'] = idTagihan
            data['totalNominal'] = totalNominal
            data['nomorJurnalPembukuan'] = nomorJurnalPembukuan

            r = requests.post(url="http://localhost:8002", data=data).json()
            print(r['rc'])

            if (r['rc'] in rc_code) :
                kode = rc_code[r['rc']]
                data2['rc'] = 'PAY-' + kode

                try :
                    r2 = circuit_breaker("http://localhost:8000/predict/", data2)
                except IOError:
                    return JsonResponse(r)
                else:
                    if r2 == 'Circuit Breaker sedang open.' :
                        return HttpResponse("Circuit Breaker sedang open.")

        return JsonResponse(r)



@circuit(failure_threshold=2, recovery_timeout=60, name="circuit_breaker", fallback_function=fallbackFunction)
def circuit_breaker(url, data):
    r = requests.post(url=url, data=data)
    if r.text == 'error' :
        raise IOError
    else :
        return r.text

        