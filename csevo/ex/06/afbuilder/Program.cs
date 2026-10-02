// 슬라이드 p6-v5-after-builder — 메서드마다 고르는 빌더, C# 10.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static async ValueTask<int> Plain()
    {
        await Task.Yield();
        return 1;
    }

    [AsyncMethodBuilder(typeof(PoolingAsyncValueTaskMethodBuilder<>))]
    static async ValueTask<int> Pooled()
    {
        await Task.Yield();
        return 2;
    }

    // Which builder did the compiler put in the state machine?
    static void Show(string name)
    {
        MethodInfo m = typeof(App).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static);
        Type sm = m.GetCustomAttribute<AsyncStateMachineAttribute>()
            .StateMachineType;
        FieldInfo b = sm.GetField("<>t__builder");
        Console.WriteLine(name + ": " + b.FieldType.Name);
    }

    static async Task Main()
    {
        Show("Plain");
        Show("Pooled");
        Console.WriteLine(await Plain() + await Pooled());
    }
}
