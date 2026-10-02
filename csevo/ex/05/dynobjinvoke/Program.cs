// 슬라이드 p5-v4-dyn-dynobj-ops — 호출·연산자·변환·인덱스, C# 4.0
using System;
using System.Dynamic;

class Echo : DynamicObject
{
    public override bool TryInvokeMember(InvokeMemberBinder binder,
        object[] args, out object result)
    {
        result = binder.Name + "(" + string.Join(", ", args)
            + ") names: "
            + string.Join(",", binder.CallInfo.ArgumentNames);
        return true;
    }
    public override bool TryBinaryOperation(
        BinaryOperationBinder binder, object arg, out object result)
    {
        result = "op " + binder.Operation + " " + arg;
        return true;
    }
    public override bool TryConvert(ConvertBinder b, out object result)
    {
        result = 42;
        return b.Type == typeof(int);
    }
    public override bool TryGetIndex(GetIndexBinder binder,
        object[] indexes, out object result)
    {
        result = "index [" + string.Join(", ", indexes) + "]";
        return true;
    }
}

class Program
{
    static void Main()
    {
        dynamic e = new Echo();
        Console.WriteLine(e.Send(1, "two", to: "you"));
        Console.WriteLine(e * 3);
        int n = e;
        Console.WriteLine(n);
        Console.WriteLine(e[1, "b"]);
    }
}
