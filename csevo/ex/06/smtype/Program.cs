// 슬라이드 p6-v5-sm — 컴파일러가 만든 상태 기계 형식, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static async Task<int> Work(int x)
    {
        await Task.Delay(1);
        return x + 1;
    }

    static async Task NoAwait() { }

    static void Show(string name)
    {
        MethodInfo m = typeof(App).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static);
        AsyncStateMachineAttribute a = (AsyncStateMachineAttribute)
            m.GetCustomAttribute(typeof(AsyncStateMachineAttribute));
        Type sm = a.StateMachineType;
        Console.WriteLine(name + " -> " + sm.Name
            + (sm.IsValueType ? " (struct)" : " (class)"));
        Console.WriteLine("  nested in " + sm.DeclaringType.Name);
        foreach (Type i in sm.GetInterfaces())
            Console.WriteLine("  implements " + i.Name);
    }

    static void Main()
    {
        Show("Work");
        Show("NoAwait");
    }
}
