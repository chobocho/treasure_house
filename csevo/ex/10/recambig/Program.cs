// 슬라이드 p10-v9-rec-ambig — record 가 이름이던 시절, C# 9.0
using System;
using System.Reflection;

class record { }

abstract class C
{
    protected abstract record R3();
}

class App
{
    static void Main()
    {
        const BindingFlags all = BindingFlags.Instance
            | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;
        foreach (MemberInfo m in typeof(C).GetMembers(all))
            Console.WriteLine(m.MemberType + " " + m.Name);
    }
}
