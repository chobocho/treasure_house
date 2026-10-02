// 슬라이드 p10-v9-fnptr-reflect — 리플렉션이 보는 함수 포인터, C# 9.0
using System;
using System.Reflection;

unsafe class Holder
{
    public delegate*<int, string> F = null;
    public delegate* unmanaged<double, void> G = null;
}

class App
{
    static void Show(FieldInfo f)
    {
        Type t = f.FieldType;
        Console.WriteLine(f.Name + ": \"" + t + "\"");
        Console.WriteLine("   IsFunctionPointer " + t.IsFunctionPointer
            + ", IntPtr? " + (t == typeof(IntPtr)));
        Console.WriteLine("   unmanaged " + t.IsUnmanagedFunctionPointer
            + ", returns " + t.GetFunctionPointerReturnType());
        foreach (Type p in t.GetFunctionPointerParameterTypes())
            Console.WriteLine("   param " + p);
    }

    static void Main()
    {
        foreach (FieldInfo f in typeof(Holder).GetFields())
            Show(f);
        object v = typeof(Holder).GetField("F").GetValue(new Holder());
        Console.WriteLine("GetValue -> " + v.GetType());
    }
}
