// 슬라이드 p8-v7-tasktype-later10 — 메서드마다 빌더 고르기, C# 10
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    [AsyncMethodBuilder(typeof(PoolingAsyncValueTaskMethodBuilder<>))]
    static async ValueTask<int> Pooled(int x)
    {
        await Task.Yield();
        return x + 1;
    }

    static async ValueTask<int> Plain(int x)
    {
        await Task.Yield();
        return x + 2;
    }

    static void Show(string name)
    {
        Type sm = typeof(App).GetMethod(name,
                BindingFlags.Static | BindingFlags.NonPublic)
            .GetCustomAttribute<AsyncStateMachineAttribute>()
            .StateMachineType;
        foreach (FieldInfo f in sm.GetFields())
            if (f.Name.Contains("builder"))
                Console.WriteLine("{0,-7} {1}", name, f.FieldType.Name);
    }

    static void Main()
    {
        Show("Pooled");
        Show("Plain");
        Console.WriteLine(Pooled(1).Result + Plain(1).Result);
    }
}
