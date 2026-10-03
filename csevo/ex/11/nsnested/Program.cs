// 슬라이드 p11-v10-ns-nested — 점으로 이은 이름은 중첩, C# 10.0
namespace Shop.Billing;

class Invoice { }

class App
{
    static void Main()
    {
        System.Console.WriteLine(typeof(Invoice).Namespace);
        System.Console.WriteLine(
            typeof(Shop.Billing.Invoice) == typeof(Invoice));
        System.Console.WriteLine(typeof(Shop.Tax).FullName);
    }
}
