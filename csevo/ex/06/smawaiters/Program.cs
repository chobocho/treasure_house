// 슬라이드 p6-v5-smawaiters — await 가 여럿이면, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static async Task<int> Three()
    {
        int a = await Task.FromResult(1);   // TaskAwaiter<int>
        await Task.Delay(1);                // TaskAwaiter
        int b = await Task.FromResult(2);   // TaskAwaiter<int> again
        return a + b;
    }

    static void Main()
    {
        MethodInfo m = typeof(App).GetMethod("Three",
            BindingFlags.NonPublic | BindingFlags.Static);
        Type sm = ((AsyncStateMachineAttribute)m.GetCustomAttribute(
            typeof(AsyncStateMachineAttribute))).StateMachineType;
        foreach (FieldInfo f in sm.GetFields(BindingFlags.Instance
            | BindingFlags.Public | BindingFlags.NonPublic))
        {
            if (f.Name.StartsWith("<>u__", StringComparison.Ordinal))
                Console.WriteLine(f.Name + " : " + f.FieldType.Name);
        }
        Console.WriteLine(Three().Result);
    }
}
