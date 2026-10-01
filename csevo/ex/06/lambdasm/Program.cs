// 슬라이드 p6-v5-lambdasm — async 람다의 상태 기계는 어디에, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static void Main()
    {
        Func<int, Task<int>> f =
            async x => await Task.FromResult(x) + 1;
        MethodInfo m = f.Method;        // the method the lambda became
        Console.WriteLine("lambda body: " + m.DeclaringType.Name
            + "." + m.Name);
        AsyncStateMachineAttribute a = (AsyncStateMachineAttribute)
            m.GetCustomAttribute(typeof(AsyncStateMachineAttribute));
        Console.WriteLine("state machine: " + a.StateMachineType.Name
            + " in " + a.StateMachineType.DeclaringType.Name);
        Console.WriteLine("result: " + f(41).Result);
    }
}
