// 슬라이드 p12-v11-rf-null — default 의 ref 필드는 null ref, C# 11
using System;
using System.Runtime.CompilerServices;

ref struct S1                     // the proposal's S1
{
    private ref int Value;
    public S1(ref int v) { Value = ref v; }

    public int GetValue()
    {
        if (Unsafe.IsNullRef(ref Value))
            throw new InvalidOperationException("default S1");
        return Value;
    }

    public int Raw => Value;      // no check
}

class Program
{
    static void Main()
    {
        int x = 3;
        Console.WriteLine(new S1(ref x).GetValue());
        S1 d = default;
        try { d.GetValue(); }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("checked  : " + e.Message);
        }
        try { Console.WriteLine(d.Raw); }
        catch (NullReferenceException e)
        {
            Console.WriteLine("unchecked: " + e.GetType().Name);
        }
    }
}
