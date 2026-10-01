// 슬라이드 p6-v5-smbuilders — 반환 형식마다 빌더가 다르다, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static async void V() { await Task.FromResult(0); }
    static async Task T() { await Task.FromResult(0); }
    static async Task<int> TI() { return await Task.FromResult(0); }

    static void Show(string name)
    {
        MethodInfo m = typeof(App).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static);
        Type sm = ((AsyncStateMachineAttribute)m.GetCustomAttribute(
            typeof(AsyncStateMachineAttribute))).StateMachineType;
        FieldInfo b = sm.GetField("<>t__builder");
        Console.WriteLine("{0,-17} {1}", m.ReturnType.Name + " " + name,
            b.FieldType.Name);
    }

    static void Main()
    {
        Show("V");
        Show("T");
        Show("TI");
    }
}
