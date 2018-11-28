''' Calculates voltages on the transformer LV
Used for determining appropriate transformer tap range
'''
import powerfactory as pf
import pandas as pd

def main():
    '''The main function'''

    app = pf.GetApplication()
    selection = app.GetDiagramSelection()
    #It is expected that the user would select the generator, transformer
    # LV bus, and external grid to be tested
    #get transformer, LV bus, external grid, and generator

    #pre assignments so that the assertion checks work
    tx = None
    sym = None
    xnet = None
    bus = None

    for obj in selection:
        if obj.GetClassName() == "ElmTr2":
            tx = obj
        elif obj.GetClassName() == "ElmSym":
            sym = obj
        elif obj.GetClassName() == "ElmXnet":
            xnet = obj
        elif obj.GetClassName() == "ElmTerm":
            bus = obj

    #some assertions to make sure we have everything
    assert tx, "Error, no transformer found in selection."
    assert sym, "Error, no synchronous machine found in selection"
    assert xnet, "Error, no external grid found in selection"
    assert bus, "Error, no bus found in selection"

    #sys.exit()
    #Get loadflow command
    ldf = app.GetFromStudyCase('ComLdf')
    #shc.Execute()
    test_points = {1.1:[-1/3, 1/2], 0.95:[-1/3], 0.9:[1/2]}

    app.EchoOff()
    results = {}
    for voltage in test_points:
        #set ElmXnet
        xnet.usetp = voltage
        sym.pgini = sym.GetAttribute("t:sgn") * sym.GetAttribute("t:cosn")
        reactive_lims = {}
        for reactive in test_points[voltage]:
            sym.qgini = sym.GetAttribute("t:sgn") * sym.GetAttribute("t:cosn") \
             * reactive
            reactive_lims[reactive] = {}
            for tap in range(1, 10):
                tx.nntap = tap
                ldf.Execute()
                reactive_lims[reactive][tap] = bus.GetAttribute('m:u')
        results[voltage] = reactive_lims

    #below creates the DataFrame with a multiindex
    df = pd.DataFrame.from_dict({(i,j): results[i][j]
                                 for i in results
                                 for j in results[i]})
    app.PrintPlain(df)
    df.to_csv('tapresults.csv')
    #app.PrintPlain(results)#save results

if __name__ == '__main__':
    main()
