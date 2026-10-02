// 슬라이드 p5-v4-dyn-dynobj — DynamicObject 로 가로채기, C# 4.0
using System;
using System.Collections.Generic;
using System.Dynamic;
using Microsoft.CSharp.RuntimeBinder;

class Bag : DynamicObject
{
    Dictionary<string, object> data = new Dictionary<string, object>();

    public override bool TryGetMember(GetMemberBinder binder,
                                      out object result)
    {
        Console.WriteLine("  TryGetMember " + binder.Name);
        return data.TryGetValue(binder.Name, out result);
    }

    public override bool TrySetMember(SetMemberBinder binder,
                                      object value)
    {
        Console.WriteLine("  TrySetMember " + binder.Name);
        data[binder.Name] = value;
        return true;
    }
}

class Program
{
    static void Main()
    {
        dynamic b = new Bag();
        b.Color = "red";
        Console.WriteLine(b.Color);
        try { Console.WriteLine(b.Size); }
        catch (RuntimeBinderException e) {
            Console.WriteLine(e.Message); }
    }
}
