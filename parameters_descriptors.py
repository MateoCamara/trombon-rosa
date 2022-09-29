def getParameterDescriptors():

    ParameterDescriptors = [
        {
            "name": "noise",
            "defaultValue": 0,
            "minValue": -1,
            "maxValue": 1,
        },
        {
            "name": "frequency",
            "defaultValue": 140,
            "minValue": 0,
        },
        {
            "name": "tenseness",
            "defaultValue": 0.6,
            "minValue": 0,
            "maxValue": 1,
        },
        {
            "name": "intensity",
            "defaultValue": 1,
            "minValue": 0,
            "maxValue": 1,
        },
        {
            "name": "loudness",
            "defaultValue": 1,
            "minValue": 0,
            "maxValue": 1,
        },
        {
            "name": "tongueIndex",
            "defaultValue": 12.9,
        },
        {
            "name": "tongueDiameter",
            "defaultValue": 2.43,
        },
        {
            "name": "vibratoWobble",
            "defaultValue": 1,
            "minValue": 0,
            "maxValue": 1,
        },
        {
            "name": "vibratoFrequency",
            "defaultValue": 6,
            "minValue": 0,
        },
        {
            "name": "vibratoGain",
            "defaultValue": 0.005,
            "minValue": 0,
        },
    ]

    # numberOfConstrictions = 4
    # constrictionParameterDescriptors = []
    #
    # for i in range(numberOfConstrictions):
    #     constrictionParameterDescriptors.append({
    #         "index": "constriction" + str(i) + "index",
    #         "diameter": 0,
    #     })

    ParameterDescriptors = {i['name']: i['defaultValue'] for i in ParameterDescriptors}

    return ParameterDescriptors