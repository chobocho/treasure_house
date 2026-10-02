// 슬라이드 p5-v4-com-ref — COM 메서드에서는 ref 를 생략, C# 4.0
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("6B29FC40-CA47-1067-B31D-00DD010662DA")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IComDoc
{
    void Save(ref object fileName, ref object format);
}

interface IPlainDoc
{
    void Save(ref object fileName, ref object format);
}

class Program
{
    static void UseCom(IComDoc doc)
    {
        doc.Save("a.doc", 0);      // no 'ref', no temp variables
    }

#if BAD
    static void UsePlain(IPlainDoc doc)
    {
        doc.Save("a.doc", 0);              // not a COM interface
    }
#endif

    static void Main()
    {
        Console.WriteLine(typeof(IComDoc).IsImport);
        Console.WriteLine(typeof(IPlainDoc).IsImport);
    }
}
