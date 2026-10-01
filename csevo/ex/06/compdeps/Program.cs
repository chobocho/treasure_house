// 슬라이드 p6-v5-compdeps — 컴파일러가 기대는 형식, C# 5.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static void Show(Type t)
    {
        Console.WriteLine("{0,-30} {1}", t.Name,
            t.Assembly.GetName().Name);
    }

    static void Main()
    {
        Show(typeof(Task));
        Show(typeof(Task<>));
        Show(typeof(AsyncVoidMethodBuilder));
        Show(typeof(AsyncTaskMethodBuilder));
        Show(typeof(AsyncTaskMethodBuilder<>));
        Show(typeof(IAsyncStateMachine));
        Show(typeof(INotifyCompletion));
        Show(typeof(ICriticalNotifyCompletion));
        Show(typeof(TaskAwaiter));
        Show(typeof(AsyncStateMachineAttribute));
        Type[] its = typeof(TaskAwaiter).GetInterfaces();
        Array.Sort(its,
            (x, y) => string.CompareOrdinal(x.Name, y.Name));
        foreach (Type i in its)
            Console.WriteLine("TaskAwaiter implements " + i.Name);
    }
}
