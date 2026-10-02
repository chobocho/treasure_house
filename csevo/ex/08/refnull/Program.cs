// 슬라이드 p8-v7-ref-null — 아무 데도 안 가리키는 ref 와 _ = r, C# 7.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        ref int r = ref Unsafe.NullRef<int>();
        Console.WriteLine("IsNullRef: " + Unsafe.IsNullRef(ref r));
        try
        {
            _ = r;                   // read the value and drop it
            Console.WriteLine("_ = r ignored");
        }
        catch (NullReferenceException)
        {
            Console.WriteLine("_ = r read it: NullReferenceException");
        }
    }
}
