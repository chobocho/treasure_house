// 슬라이드 p8-v7-tasktype — 작업 같은 형식과 빌더 특성, C# 7.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static async ValueTask<int> Twice(int x)
    {
        await Task.Yield();
        return x * 2;
    }

    static void Main()
    {
        Type[] types = { typeof(Task), typeof(Task<>),
            typeof(ValueTask), typeof(ValueTask<>) };
        foreach (Type t in types)
        {
            var a = t.GetCustomAttribute<AsyncMethodBuilderAttribute>();
            Console.WriteLine("{0,-12} {1}", t.Name,
                a == null ? "(no attribute)" : a.BuilderType.Name);
        }

        Type sm = typeof(App).GetMethod("Twice",
                BindingFlags.Static | BindingFlags.NonPublic)
            .GetCustomAttribute<AsyncStateMachineAttribute>()
            .StateMachineType;
        foreach (FieldInfo f in sm.GetFields())
            if (f.Name.Contains("builder"))
                Console.WriteLine("{0}: {1}", f.Name, f.FieldType.Name);
        Console.WriteLine(Twice(21).Result);
    }
}
