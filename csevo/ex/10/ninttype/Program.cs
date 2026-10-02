// 슬라이드 p10-v9-nint-type — nint 의 런타임 형식, C# 9.0
using System;
using System.Reflection;

class Holder
{
    public nint N = 1;
    public IntPtr P = (IntPtr)2;
}

class App
{
    static void Main()
    {
        nint n = 7;
        Console.WriteLine(typeof(nint) == typeof(IntPtr));
        Console.WriteLine(n.GetType().FullName);
        foreach (FieldInfo f in typeof(Holder).GetFields())
        {
            string attrs = "";
            foreach (var a in f.GetCustomAttributesData())
                attrs += " [" + a.AttributeType.Name + "]";
            Console.WriteLine(f.Name + ": " + f.FieldType.Name + attrs);
        }
    }
}
