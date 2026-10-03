// 슬라이드 p12-v11-ni-dyn — dynamic 이 아는 IntPtr 연산, C# 11.0
using System;

class App
{
    static void Main()
    {
        nint x = 2;
        Console.WriteLine(x + x);                 // compiler: built-in
        // What the runtime binder can see: operators declared on IntPtr
        foreach (var m in typeof(IntPtr).GetMethods())
            if (m.Name == "op_Addition") Console.WriteLine(m);
        dynamic d = x;
        Console.WriteLine(d + 1);
        try { Console.WriteLine(d + x); }         // IntPtr + IntPtr
        catch (Exception e) { Console.WriteLine(e.Message); }
    }
}
