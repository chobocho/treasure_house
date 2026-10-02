// 슬라이드 p5-v4-nopia-attr — 내장 interop 형식이 기대는 특성, C# 4.0
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

class Program
{
    static void Main()
    {
        Type[] types = {
            typeof(TypeIdentifierAttribute),
            typeof(ComImportAttribute),
            typeof(GuidAttribute),
            typeof(ImportedFromTypeLibAttribute),
            typeof(PrimaryInteropAssemblyAttribute),
            typeof(ComEventInterfaceAttribute),
        };
        foreach (Type t in types)
        {
            Console.WriteLine("{0,-58} {1}", t.FullName,
                              t.Assembly.GetName().Name);
        }
        Console.WriteLine(typeof(Type).GetMethod("IsEquivalentTo"));
    }
}
