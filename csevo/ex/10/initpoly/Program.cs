// 슬라이드 p10-v9-init-poly — IsExternalInit 을 직접 선언하면, C# 9.0
using System;
using System.Reflection;

namespace System.Runtime.CompilerServices
{
    // same full name as the type in System.Private.CoreLib
    internal static class IsExternalInit { }
}

class Person
{
    public string Name { get; init; }
}

class App
{
    static void Main()
    {
        MethodInfo set = typeof(Person).GetProperty("Name").SetMethod;
        Type mod = set.ReturnParameter.GetRequiredCustomModifiers()[0];
        Console.WriteLine(mod.FullName);
        Console.WriteLine(mod.Assembly.GetName().Name);
        Console.WriteLine(typeof(object).Assembly.GetType(
            "System.Runtime.CompilerServices.IsExternalInit") != null);
        Console.WriteLine(new Person { Name = "ann" }.Name);
    }
}
