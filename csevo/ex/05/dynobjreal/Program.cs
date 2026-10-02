// 슬라이드 p5-v4-dyn-dynobj-real — 진짜 멤버가 먼저다, C# 4.0
using System;
using System.Dynamic;

class Mixed : DynamicObject
{
    public string Real = "real field";

    public override bool TryGetMember(GetMemberBinder binder,
                                      out object result)
    {
        result = "TryGetMember(" + binder.Name + ")";
        return true;
    }
}

class Program
{
    static void Main()
    {
        dynamic m = new Mixed();
        Console.WriteLine(m.Real);
        Console.WriteLine(m.Fake);
        Console.WriteLine(m.real);      // C# binding is case-sensitive
    }
}
