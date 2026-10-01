// 슬라이드 p6-v5-sm-fields — 지역 변수는 필드로 옮겨진다, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    int bonus = 100;

    async Task<int> Work(int x)
    {
        int before = x * 2;             // used only before the await
        int kept = x * 3;               // used after the await
        Console.WriteLine("before = " + before);
        await Task.Delay(1);
        return kept + bonus;
    }

    static void Main()
    {
        MethodInfo m = typeof(App).GetMethod("Work",
            BindingFlags.NonPublic | BindingFlags.Instance);
        Type sm = ((AsyncStateMachineAttribute)m.GetCustomAttribute(
            typeof(AsyncStateMachineAttribute))).StateMachineType;
        foreach (FieldInfo f in sm.GetFields(BindingFlags.Instance
            | BindingFlags.Public | BindingFlags.NonPublic))
        {
            Console.WriteLine("  " + f.Name + " : " + f.FieldType.Name);
        }
        Console.WriteLine(new App().Work(1).Result);
    }
}
