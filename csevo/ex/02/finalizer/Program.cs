// 슬라이드 p2-v1-finalizer — 소멸자는 Finalize 가 된다, C# 1.0
using System;
using System.Reflection;

class Handle
{
    ~Handle()
    {
        Console.WriteLine("finalizing");
    }
}

class App
{
    static void Main()
    {
        MethodInfo f = typeof(Handle).GetMethod("Finalize",
            BindingFlags.Instance | BindingFlags.NonPublic
            | BindingFlags.DeclaredOnly);
        Console.WriteLine("declared:  " + f.Name);
        Console.WriteLine("protected: " + f.IsFamily);
        Console.WriteLine("virtual:   " + f.IsVirtual);
        Console.WriteLine("overrides: "
            + f.GetBaseDefinition().DeclaringType.FullName);
    }
}
