// 슬라이드 p8-v7-ref-meta — ref 반환의 정체는 관리 포인터 형식, C# 7.0
using System;
using System.Reflection;

delegate ref int RefGetter(int i);

class App
{
    static int[] data = { 10, 20, 30 };

    static ref int At(int i) { return ref data[i]; }

    static void Main()
    {
        MethodInfo m = typeof(App).GetMethod("At",
            BindingFlags.Static | BindingFlags.NonPublic);
        Type t = m.ReturnType;
        Console.WriteLine("{0} IsByRef={1} element={2}",
            t, t.IsByRef, t.GetElementType());

        RefGetter g = At;              // a delegate that returns ref
        g(1) = 21;
        Console.WriteLine(data[1]);

        object boxed = m.Invoke(null, new object[] { 2 });
        Console.WriteLine("Invoke -> {0} ({1})", boxed,
            boxed.GetType().Name);
#if BAD
        Func<int, int> f = At;         // Func returns by value
#endif
    }
}
